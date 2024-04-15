import sys
import cv2
from cv2 import aruco
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

class ArucoGenerator(QWidget):
    def __init__(self):
        super().__init__()
        # 先初始化 aruco_dict 属性
        self.aruco_dict = aruco.DICT_6X6_250  # 使用默认字典
        self.init_ui()  # 然后调用 init_ui 方法

    def init_ui(self):
        self.setWindowTitle("ArUco Marker Generator")
        self.layout = QVBoxLayout(self)

        # Dropdown to select ArUco dictionary
        self.dictionary_selector = QComboBox(self)
        self.dictionary_selector.addItems([
            'DICT_4X4_50', 'DICT_4X4_100', 'DICT_4X4_250', 'DICT_4X4_1000',
            'DICT_5X5_50', 'DICT_5X5_100', 'DICT_5X5_250', 'DICT_5X5_1000',
            'DICT_6X6_50', 'DICT_6X6_100', 'DICT_6X6_250', 'DICT_6X6_1000',
            'DICT_7X7_50', 'DICT_7X7_100', 'DICT_7X7_250', 'DICT_7X7_1000',
            'DICT_ARUCO_ORIGINAL'
        ])
        self.dictionary_selector.currentIndexChanged.connect(self.update_dictionary)
        self.layout.addWidget(self.dictionary_selector)

        # Label to show the marker image
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        # Button to save the marker
        self.save_button = QPushButton("Save Marker", self)
        self.save_button.clicked.connect(self.save_marker)
        self.layout.addWidget(self.save_button)

        self.generate_marker()  # Generate initial marker after everything is set up

    def update_dictionary(self):
        dictionary_name = self.dictionary_selector.currentText()
        self.aruco_dict = getattr(aruco, dictionary_name)
        self.generate_marker()

    def generate_marker(self):
        dictionary = aruco.getPredefinedDictionary(self.aruco_dict)
        marker_image = aruco.generateImageMarker(dictionary, 0, 400)  # Marker ID 0, 400x400 pixels
        self.show_marker(marker_image)

    def show_marker(self, marker_image):
        q_image = QImage(marker_image.data, marker_image.shape[1], marker_image.shape[0], QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

    def save_marker(self):
        # Get the current dictionary name from the combo box
        dictionary_name = self.dictionary_selector.currentText()

        # Set the default file name based on the selected dictionary
        default_file_name = f"{dictionary_name}.png"  # Assuming PNG format, you can change it as needed

        # Open a file dialog with the default file name
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Marker", default_file_name,
                                                   "PNG Files (*.png);;JPG Files (*.jpg);;All Files (*)")
        if file_path:
            dictionary = aruco.getPredefinedDictionary(self.aruco_dict)
            # Generate the marker image
            marker_image = aruco.generateImageMarker(dictionary, 0,
                                            400)
            cv2.imwrite(file_path, marker_image)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArucoGenerator()
    window.show()
    sys.exit(app.exec())
