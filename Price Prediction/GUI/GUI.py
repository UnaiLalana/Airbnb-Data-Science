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
    QFormLayout, QComboBox, QTextEdit, QTabWidget, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QSize

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
        self.n_rooms.addItems([str(i) for i in range(1, 11)])  # Common range 1-10 rooms
        self.n_rooms.insertItem(0, "")  # Add an empty option as default
        self.n_rooms.setCurrentIndex(0)
        self.n_rooms.setEditable(True)  # Allow typing, but mainly for selection
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
                       f"  Amenities: {user_data.get('amenities_str', 'N/A')}\n" \
                       f"  Property Type: {user_data.get('property_type', 'N/A')}\n" \
                       f"  Room Type: {user_data.get('room_type', 'N/A')}"
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

            if input_df is None:
                prediction_label.setText(f"<span style='color:red;'>Error preparing input for prediction.</span>")
                return

            # Ensure all columns in ALL_TRAINING_COLUMNS are present, fill missing with 0
            # This is crucial for LightGBM
            for col in ALL_TRAINING_COLUMNS:
                if col not in input_df.columns:
                    input_df[col] = 0

            # Reorder columns to match training order (important for some models)
            input_df = input_df[ALL_TRAINING_COLUMNS]

            # Make prediction
            predicted_price = self.model.predict(input_df)[0]

            # Display the prediction
            prediction_label.setText(f"<b>Predicted Price: SEK {predicted_price:,.2f}</b>")
            prediction_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #008000; margin-top: 20px;")

        except Exception as e:
            error_msg = f"Error during prediction: {e}"
            print(error_msg)
            prediction_label.setText(f"<span style='color:red;'>Error: Could not make prediction. {e}</span>")
            self._show_error_message(error_msg)  # Also show in a dialog

        layout.addStretch()  # Push content up

        # Add the new result tab and switch to it
        tab_index = self.tabs.addTab(result_tab_widget,
                                     f"Result {self.tabs.count()}")
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
        Prepares a pandas DataFrame with all necessary features for the LightGBM model.
        Fills in default/dummy values for features not collected from the UI.
        """
        # Create a DataFrame with all training columns, initialized to 0
        input_df = pd.DataFrame(0, index=[0], columns=ALL_TRAINING_COLUMNS)

        # --- Handle User Input Features ---
        input_df['accommodates'] = user_data['n_rooms']  # A rough approximation, could be refined
        input_df['bedrooms'] = user_data['n_rooms']  # Assuming 1 bedroom per room for simplicity
        input_df['beds'] = user_data['n_rooms']  # Assuming 1 bed per room for simplicity

        # Geocoding and Neighborhood
        latitude, longitude = self._get_coordinates(user_data['address'])
        if latitude is None or longitude is None:
            self._show_error_message("Could not get coordinates for the given address. Please check the address.")
            return None
        input_df['latitude'] = latitude
        input_df['longitude'] = longitude

        neighborhood = self._get_neighborhood(latitude, longitude)
        # Sanitize neighborhood name for column name
        sanitized_neighborhood = re.sub(r'[^a-zA-Z0-9_]', '_', neighborhood).replace('__', '_').strip('_')
        neighborhood_col = f'neighbourhood_cleansed_{sanitized_neighborhood}'

        if neighborhood_col in ALL_TRAINING_COLUMNS:
            input_df[neighborhood_col] = 1
        else:
            print(
                f"Warning: Neighborhood '{neighborhood}' (sanitized to '{sanitized_neighborhood}') not found in training columns. It will be treated as an unknown neighborhood.")
            # If the neighborhood is not in the training columns, it effectively stays 0 for that specific dummy variable, which is correct.

        # Property Type
        # Sanitize property type for column name
        property_type_clean = user_data['property_type'].replace(" ", "_").replace("/", "_").replace("-", "_").lower()

        # Handle "Entire home/apt" as a special case for property_type to map to 'Entire_home' or 'Entire_rental_unit'
        if property_type_clean == "entire_home/apt":
            # Heuristic: assume 'Entire_home' if common, or 'Entire_rental_unit'
            if 'property_type_Entire_home' in ALL_TRAINING_COLUMNS:
                input_df['property_type_Entire_home'] = 1
            elif 'property_type_Entire_rental_unit' in ALL_TRAINING_COLUMNS:
                input_df['property_type_Entire_rental_unit'] = 1
            else:
                print(f"Warning: Could not map 'Entire home/apt' to a known property type column.")
        else:
            # Map other property types
            property_type_col = f'property_type_{property_type_clean.capitalize()}'  # Assume capitalized first letter
            if property_type_col in ALL_TRAINING_COLUMNS:
                input_df[property_type_col] = 1
            else:
                # Try a direct match if capitalization is different in ALL_TRAINING_COLUMNS
                found = False
                for col in ALL_TRAINING_COLUMNS:
                    if col.startswith('property_type_') and col.lower() == f'property_type_{property_type_clean}':
                        input_df[col] = 1
                        found = True
                        break
                if not found:
                    print(
                        f"Warning: Property type '{user_data['property_type']}' (sanitized to '{property_type_clean}') not found in training columns.")

        # Room Type
        room_type_clean = user_data['room_type'].replace(" ", "_").replace("/", "_").replace("-", "_").lower()
        if room_type_clean == "entire_home_apt":
            # Map "Entire home/apt" to 'Entire_home_apt' (if it exists) or 'Entire_home' for 'room_type'
            if 'room_type_Entire_home_apt' in ALL_TRAINING_COLUMNS:
                input_df['room_type_Entire_home_apt'] = 1
            elif 'room_type_Entire_home' in ALL_TRAINING_COLUMNS:  # Fallback if 'Entire_home_apt' isn't exact
                input_df['room_type_Entire_home'] = 1
            else:
                print(f"Warning: Could not map 'Entire home/apt' to a known room type column.")
        else:
            room_type_col = f'room_type_{room_type_clean.capitalize()}'  # Assume capitalized first letter
            if room_type_col in ALL_TRAINING_COLUMNS:
                input_df[room_type_col] = 1
            else:
                # Try a direct match if capitalization is different in ALL_TRAINING_COLUMNS
                found = False
                for col in ALL_TRAINING_COLUMNS:
                    if col.startswith('room_type_') and col.lower() == f'room_type_{room_type_clean}':
                        input_df[col] = 1
                        found = True
                        break
                if not found:
                    print(
                        f"Warning: Room type '{user_data['room_type']}' (sanitized to '{room_type_clean}') not found in training columns.")

        # Amenities
        amenities_list = [a.strip().lower() for a in user_data['amenities_str'].split(',') if a.strip()]
        for amenity in amenities_list:
            # Sanitize amenity name for column name
            sanitized_amenity = re.sub(r'[^a-zA-Z0-9_]', '_', amenity).replace('__', '_').strip('_')
            amenity_col = sanitized_amenity

            # Check if the amenity (sanitized) is in our training columns
            if amenity_col in ALL_TRAINING_COLUMNS:
                input_df[amenity_col] = 1
            else:
                print(
                    f"Warning: Amenity '{amenity}' (sanitized to '{sanitized_amenity}') not found in training columns. It will be ignored.")

        # --- Fill in default/dummy values for other features (crucial for model compatibility) ---
        # Many of these are binary (0/1) or numerical features that we haven't exposed in the UI.
        # For simplicity, we'll initialize them to reasonable defaults (e.g., 0 for counts/rates, 0 for binary flags).
        # In a real-world scenario, you might have more sophisticated imputation or default values.

        # Numerical features - set to mean/median from training data if known, otherwise 0 or a sensible default
        input_df['host_since'] = 0  # Placeholder: Days since host joined (or datetime converted to numeric)
        input_df['host_response_rate'] = 0.5  # Default (e.g., 1.0 or 0.9 depending on typical values)
        input_df['host_acceptance_rate'] = 0.7  # Default (e.g., 1.0 or 0.9 depending on typical values)
        input_df['host_listings_count'] = 1  # Default: at least 1 listing
        input_df['host_total_listings_count'] = 1  # Default: at least 1 listing
        input_df['minimum_nights'] = 2  # Common default
        input_df['maximum_nights'] = 1125  # A common high value (e.g., 3 years)
        input_df['availability_30'] = 30  # Assume unavailable by default if not specified
        input_df['availability_60'] = 60
        input_df['availability_90'] = 90
        input_df['availability_365'] = 365
        input_df['number_of_reviews'] = 0  # New listing
        input_df['review_scores_rating'] = 3.84  # No reviews yet
        input_df['review_scores_accuracy'] = 3.84
        input_df['review_scores_cleanliness'] = 3.80
        input_df['review_scores_checkin'] = 3.88
        input_df['review_scores_communication'] = 3.89
        input_df['review_scores_location'] = 3.85
        input_df['review_scores_value'] = 3.77
        input_df['calculated_host_listings_count'] = 1
        input_df['reviews_per_month'] = 0
        input_df['host_duration_days'] = 0
        input_df['num_bathrooms'] = 1  # Common default
        input_df['num_amenities'] = len(amenities_list)  # Count of user-provided amenities
        input_df['num_host_verifications'] = 0  # No info on this
        input_df['days_since_last_review'] = 0
        input_df['days_since_first_review'] = 0
        input_df['desc_sentiment'] = 0.5  # Assuming neutral sentiment if no description or not analyzed

        # Binary features (flags) - set to 0 (False) unless explicitly handled
        input_df['host_is_superhost'] = 0
        input_df['host_has_profile_pic'] = 1  # Assume true by default for a valid host
        input_df['host_identity_verified'] = 0
        input_df['instant_bookable'] = 0
        input_df['is_shared_bath'] = 0
        input_df['never_reviewed'] = 1  # True if number_of_reviews is 0

        # Set specific default values for features that might be problematic if zero
        # (e.g., if a feature like 'kitchen' implies existence)
        if 'kitchen' in amenities_list and 'kitchen' in ALL_TRAINING_COLUMNS:
            input_df['kitchen'] = 1

        return input_df

    def _show_error_message(self, message):
        """Displays an error message in a QMessageBox."""
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