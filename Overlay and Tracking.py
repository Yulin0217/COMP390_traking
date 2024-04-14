import platform
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QFileDialog, QPushButton, QComboBox, QApplication, QWidget, QColorDialog, \
    QVBoxLayout, QMessageBox
from modified_video_source import TimestampedVideoSource
from sksurgeryvtk.widgets.vtk_overlay_window import VTKOverlayWindow
import sys
import numpy
from sksurgerycore.transforms.transform_manager import TransformManager
from sksurgeryarucotracker.arucotracker import ArUcoTracker
from model_loader import ModelDirectoryLoader
import numpy as np


class BaseWidget(QWidget):
    def __init__(self, video_source, dims=None):
        super().__init__()
        # Setup the layout for the widget
        self.color_button = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Initialize the VTK overlay window, conditionally based on the OS
        init_vtk_widget = platform.system() != 'Linux'
        self.vtk_overlay_window = VTKOverlayWindow(offscreen=False, init_widget=init_vtk_widget)
        self.layout.addWidget(self.vtk_overlay_window)

        # Initialize the video source
        self.video_source = TimestampedVideoSource(video_source, dims)

        # Set up a timer to update the view periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_view)
        self.update_rate = 30
        self.model_dir = None
        # Setup additional controls
        self.setup_upload_button()
        self.setup_video_source_controls()
        self.setup_color_change_button()

    def start(self):
        # Start the timer with a frequency based on update_rate
        self.timer.start(1000.0 / self.update_rate)

    def stop(self):
        # Stop the timer
        self.timer.stop()

    def terminate(self):
        # Properly terminate the VTK interactions
        self.vtk_overlay_window.terminate()

    def add_vtk_models_from_dir(self, directory):
        # Load and add VTK models from a directory
        model_loader = ModelDirectoryLoader(directory)
        self.vtk_overlay_window.add_vtk_models(model_loader.models)

    def update_view(self):
        # Abstract method to update the view, must be implemented in subclasses
        raise NotImplementedError('Should have implemented this method.')

    def setup_upload_button(self):
        # Setup the upload model button
        self.upload_button = QPushButton("Upload model")
        self.layout.addWidget(self.upload_button)
        self.upload_button.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        # Open a file dialog to select the directory of models
        self.model_dir = QFileDialog.getExistingDirectory(self, "Select model directory")
        if self.model_dir:
            self.add_vtk_models_from_dir(self.model_dir)

    def setup_video_source_controls(self):
        # Setup video source controls
        self.video_source_selector = QComboBox()
        self.video_source_selector.addItems(["Camera 1", "Camera 2", "Upload Video File"])
        self.layout.addWidget(self.video_source_selector)

        # Setup the upload video file button
        self.upload_video_button = QPushButton("Upload Video File")
        self.upload_video_button.clicked.connect(self.upload_video)
        self.upload_video_button.setVisible(False)  # Hidden by default
        self.layout.addWidget(self.upload_video_button)

        # Handle changes in the video source selector
        self.video_source_selector.currentIndexChanged.connect(self.handle_video_source_change)

    def handle_video_source_change(self, index):
        # Toggle the visibility of the upload video button based on selection
        self.upload_video_button.setVisible(self.video_source_selector.currentText() == "Upload Video File")

    def upload_video(self):
        # Open a file dialog to select a video file
        video_file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi)")
        if video_file_path:
            self.change_video_source(video_file_path)

    def change_video_source(self, new_source):
        # Change the video source and restart the view update process
        self.stop()
        self.video_source.update_source(new_source)
        self.start()

    def setup_color_change_button(self):
        # Adds a button to change model colors
        self.color_button = QPushButton("Change Model Color")
        self.layout.addWidget(self.color_button)
        self.color_button.clicked.connect(self.change_model_color)

    def change_model_color(self):
        # Check if models have been loaded
        if not hasattr(self, 'model_dir') or not self.model_dir:
            QMessageBox.warning(self, "No Models Loaded", "Please upload models first.")
            return

        # Opens a color picker dialog and applies the selected color to models
        color = QColorDialog.getColor()
        if color.isValid():
            rgb_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            model_loader = ModelDirectoryLoader(self.model_dir, rgb_color)
            self.vtk_overlay_window.add_vtk_models(model_loader.models)
            self.vtk_overlay_window.Render()  # Re-render the window to update the color


class OverlayBaseWidget(BaseWidget):
    def __init__(self, image_source):
        # Initialize the base class with the provided image source.
        super().__init__(image_source)

        # Configure the ArUco tracker with specific parameters for tracking.
        ar_config = {
            "tracker type": "aruco",  # Specifies the type of tracker to use.
            "video source": 'none',  # Indicates that no separate video source will be used.
            "debug": False,  # Debug mode is turned off.
            "aruco dictionary": 'DICT_4X4_50',  # Specifies the dictionary of ArUco tags.
            "marker size": 50,  # The size of the ArUco marker in mm.
            "camera projection": numpy.array([[560.0, 0.0, 320.0],
                                              [0.0, 560.0, 240.0],
                                              [0.0, 0.0, 1.0]],
                                             dtype=numpy.float32),  # Camera projection matrix.
            "camera distortion": numpy.zeros((1, 4), numpy.float32)  # Camera distortion coefficients.
        }
        self.tracker = ArUcoTracker(ar_config)
        self.tracker.start_tracking()  # Start the ArUco tracker.

    def update_view(self):
        # Updates the view by capturing the latest video frame and processing it.
        _, image, _ = self.video_source.read()  # Read a frame from the video source.
        self._aruco_detect_and_follow(image)  # Detect and process any ArUco tags in the frame.
        self.vtk_overlay_window.set_video_image(image)  # Set the video image on the VTK overlay window.
        self.vtk_overlay_window.set_camera_state({"ClippingRange": [10, 800]})  # Adjust the camera's clipping range.
        self.vtk_overlay_window.Render()  # Render the updated image in the VTK overlay window.

        # Initialize the VTK window if it hasn't been initialized already.
        if not hasattr(self, 'initialized'):
            self.vtk_overlay_window.Initialize()  # Initialize the VTK window.
            self.initialized = True  # Set the initialized flag to True.

    def _aruco_detect_and_follow(self, image):
        # Detect ArUco markers in the provided image and follow them.
        _port_handles, _timestamps, _frame_numbers, tag2camera, _tracking_quality = self.tracker.get_frame(image)
        if tag2camera:
            self._move_camera(tag2camera[0])  # Adjust the camera based on the detected tag.

    def _move_camera(self, tag2camera):
        # Adjust the camera position based on the ArUco tag's camera transformation matrix.
        transform_manager = TransformManager()
        transform_manager.add("tag2camera", tag2camera)  # Add the transformation matrix to the manager.
        camera2tag = transform_manager.get("camera2tag")  # Get the inverse transformation matrix.
        self.vtk_overlay_window.set_camera_pose(
            camera2tag)  # Update the camera pose in the VTK window based on the transformation.


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay_widget = OverlayBaseWidget(0)
    overlay_widget.show()
    overlay_widget.start()
    sys.exit(app.exec())