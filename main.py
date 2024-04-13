import platform
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QFileDialog, QPushButton, QComboBox, QApplication, QWidget
from modified_video_source import TimestampedVideoSource
from sksurgeryvtk.widgets.vtk_overlay_window import VTKOverlayWindow
import sys
import numpy
from sksurgerycore.transforms.transform_manager import TransformManager
from sksurgeryarucotracker.arucotracker import ArUcoTracker
from sksurgeryvtk.models.vtk_surface_model_directory_loader import VTKSurfaceModelDirectoryLoader

class BaseWidget(QWidget):
    def __init__(self, video_source, dims=None):
        super().__init__()
        # Setup the layout for the widget
        self.layout = QHBoxLayout(self)
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

        # Setup additional controls
        self.setup_upload_button()
        self.setup_video_source_controls()

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
        model_loader = VTKSurfaceModelDirectoryLoader(directory)
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
        model_dir = QFileDialog.getExistingDirectory(self, "Select model directory")
        if model_dir:
            self.add_vtk_models_from_dir(model_dir)

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

class OverlayBaseWidget(BaseWidget):
    def __init__(self, image_source):
        super().__init__(image_source)
        # Configuration for ArUco tracker
        ar_config = {
            "tracker type": "aruco",
            "video source": 'none',
            "debug": False,
            "aruco dictionary": 'DICT_4X4_50',
            "marker size": 50,
            "camera projection": numpy.array([[560.0, 0.0, 320.0], [0.0, 560.0, 240.0], [0.0, 0.0, 1.0]], dtype=numpy.float32),
            "camera distortion": numpy.zeros((1, 4), numpy.float32)
        }
        self.tracker = ArUcoTracker(ar_config)
        self.tracker.start_tracking()

    def update_view(self):
        # Update the view by reading from the video source, detecting ArUco markers, and rendering
        _, image, _ = self.video_source.read()
        self._aruco_detect_and_follow(image)
        self.vtk_overlay_window.set_video_image(image)
        self.vtk_overlay_window.set_camera_state({"ClippingRange": [10, 800]})
        self.vtk_overlay_window.Render()
        if not hasattr(self, 'initialized'):
            self.vtk_overlay_window.Initialize()
            self.initialized = True

    def _aruco_detect_and_follow(self, image):
        # Detect and follow ArUco tags in the image
        _port_handles, _timestamps, _frame_numbers, tag2camera, _tracking_quality = self.tracker.get_frame(image)
        if tag2camera:
            self._move_camera(tag2camera[0])

    def _move_camera(self, tag2camera):
        # Adjust the camera based on the detected tag position
        transform_manager = TransformManager()
        transform_manager.add("tag2camera", tag2camera)
        camera2tag = transform_manager.get("camera2tag")
        self.vtk_overlay_window.set_camera_pose(camera2tag)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay_widget = OverlayBaseWidget(0)
    overlay_widget.show()
    overlay_widget.start()
    sys.exit(app.exec())
