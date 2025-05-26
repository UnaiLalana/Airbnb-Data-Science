from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QFormLayout, QComboBox, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt
import sys

class ApartmentPrizePredictor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Apartment Price Predictor")
        self.setMinimumSize(600, 400)

        self.tabs = QTabWidget()
        self.form_tab = QWidget()
        self.tabs.addTab(self.form_tab, "Form")

        self.setStyleSheet("""
            QWidget {
                background-color: #EEEEEE;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                color: #1f2937;
            }
            QLabel {
                font-size: 13px;
                margin-bottom: 4px;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px 10px;
                border: 1px solid #494949;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 13px;
                color: #1f2937;
            }
            QTextEdit {
                min-height: 100px;
                max-width: 320px;
            }
            QLineEdit, QComboBox {
                min-height: 30px;
                max-width: 300px;
            }
            QComboBox QLineEdit {
                background: transparent;
                color: #1f2937;
                padding-right: 10px;
            }
            QPushButton {
                background-color: #F01C5C;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #8E053B;
            }
            QFormLayout {
                spacing: 12px;
            }
        """)

        self.init_form_tab()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_form_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Apartment Price Predictor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignCenter)

        self.address = QLineEdit()
        form_layout.addRow(QLabel("Address:"), self.address)

        self.n_rooms = QComboBox()
        self.n_rooms.addItems([str(i) for i in range(1, 16)])
        self.n_rooms.setEditable(True)
        self.n_rooms.lineEdit().setAlignment(Qt.AlignRight)
        self.n_rooms.lineEdit().setReadOnly(True)
        form_layout.addRow(QLabel("Number of rooms:"), self.n_rooms)

        self.amenities = QTextEdit()
        form_layout.addRow(QLabel("Amenities (Separate the different amenities by ,):"), self.amenities)

        layout.addLayout(form_layout)

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.show_results_tab)
        layout.addWidget(submit_button, alignment=Qt.AlignCenter)

        self.form_tab.setLayout(layout)

    def show_results_tab(self):
        result_tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        #ADD THE PROCESSING OF THE DATA TO OBTAIN THE RESULTS

        result_tab.setLayout(layout)
        self.tabs.addTab(result_tab, f"Result {self.tabs.count()}")
        self.tabs.setCurrentWidget(result_tab)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ApartmentPrizePredictor()
    window.show()
    sys.exit(app.exec())
