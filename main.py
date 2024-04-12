import platform
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QApplication, QFileDialog, QPushButton, QComboBox
from sksurgeryimage.acquire.video_source import TimestampedVideoSource
from sksurgeryvtk.widgets.vtk_overlay_window import VTKOverlayWindow
import sys
import numpy
from PySide6.QtWidgets import QApplication, QWidget
from sksurgeryutils.common_overlay_apps import OverlayBaseWidget
from sksurgerycore.transforms.transform_manager import TransformManager
from sksurgeryarucotracker.arucotracker import ArUcoTracker
from sksurgeryvtk.models.vtk_surface_model_directory_loader \
    import VTKSurfaceModelDirectoryLoader


class BaseWidget(QWidget):
    def __init__(self, video_source, dims=None, init_vtk_widget=True):
        super().__init__()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        if platform.system() == 'Linux':
            init_vtk_widget = False
        else:
            init_vtk_widget = True

        self.vtk_overlay_window = VTKOverlayWindow(offscreen=False,
                                                   init_widget=init_vtk_widget)
        self.layout.addWidget(self.vtk_overlay_window)

        self.video_source = TimestampedVideoSource(video_source, dims)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_view)

        self.update_rate = 30
        self.img = None
        self.save_frame = None
        self.setup_upload_button()
        self.setup_video_source_controls()

    def start(self):
        """
        Starts the timer, which repeatedly triggers the update_view() method.
        """
        self.timer.start(1000.0 / self.update_rate)

    def stop(self):
        """
        Stops the timer.
        """
        self.timer.stop()

    def terminate(self):
        """
        Make sure that the VTK Interactor terminates nicely, otherwise
        it can throw some error messages, depending on the usage.
        """
        self.vtk_overlay_window._RenderWindow.Finalize()  # pylint: disable=protected-access
        self.vtk_overlay_window.TerminateApp()

    def add_vtk_models_from_dir(self, directory):
        """
        Add VTK models to the foreground.
        :param: directory, location of models
        """
        model_loader = VTKSurfaceModelDirectoryLoader(directory)
        self.vtk_overlay_window.add_vtk_models(model_loader.models)

    def update_view(self):
        """ Update the scene background and/or foreground.
            Should be implemented by sub class """

        raise NotImplementedError('Should have implemented this method.')

    def add_vtk_models_from_dir(self, directory):
        """
        Add VTK models to the foreground.
        :param: directory, location of models
        """
        model_loader = VTKSurfaceModelDirectoryLoader(directory)
        self.vtk_overlay_window.add_vtk_models(model_loader.models)

    def setup_upload_button(self):
        self.upload_button = QPushButton("Upload model")
        self.layout.addWidget(self.upload_button)
        self.upload_button.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        model_dir = QFileDialog.getExistingDirectory(self, "Select index of model")
        if model_dir:
            self.add_vtk_models_from_dir(model_dir)

    def setup_video_source_controls(self):

        self.video_source_selector = QComboBox()
        self.video_source_selector.addItems(["Camera 1", "Camera 2", "Upload Video File"])
        self.layout.addWidget(self.video_source_selector)

        self.upload_video_button = QPushButton("Upload Video File")
        self.upload_video_button.clicked.connect(self.upload_video)
        self.upload_video_button.setVisible(False)
        self.layout.addWidget(self.upload_video_button)

        self.video_source_selector.currentIndexChanged.connect(self.handle_video_source_change)

    def handle_video_source_change(self, index):
        if self.video_source_selector.currentText() == "Upload Video File":
            self.upload_video_button.setVisible(True)
        else:
            self.upload_video_button.setVisible(False)

    def upload_video(self):
        video_file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi)")
        if video_file_path:
            self.change_video_source(video_file_path)


class OverlayBaseWidget(BaseWidget):

    def __init__(self, image_source):

        ar_config = {
            "tracker type": "aruco",
            "video source": 'none',
            "debug": False,
            "aruco dictionary": 'DICT_4X4_50',
            "marker size": 50,
            "camera projection": numpy.array([[560.0, 0.0, 320.0],
                                              [0.0, 560.0, 240.0],
                                              [0.0, 0.0, 1.0]],
                                             dtype=numpy.float32),
            "camera distortion": numpy.zeros((1, 4), numpy.float32)
        }
        self.tracker = ArUcoTracker(ar_config)
        self.tracker.start_tracking()

        if sys.version_info > (3, 0):
            super().__init__(image_source)
        else:
            OverlayBaseWidget.__init__(self, image_source)

    def update_view(self):
        """
        Update the background render with a new frame, scan for aruco tags,
        and ensure compatibility across different operating systems.
        """

        _, image = self.video_source.read()

        self._aruco_detect_and_follow(image)

        self.vtk_overlay_window.set_video_image(image)

        self.vtk_overlay_window.set_camera_state({"ClippingRange": [10, 800]})

        self.vtk_overlay_window.Render()
        if not hasattr(self, 'initialized'):
            self.vtk_overlay_window.Initialize()
            self.initialized = True

    def _aruco_detect_and_follow(self, image):
        """Detect any aruco tags present using sksurgeryarucotracker
        """

        _port_handles, _timestamps, _frame_numbers, tag2camera, \
            _tracking_quality = self.tracker.get_frame(image)

        if tag2camera:
            self._move_camera(tag2camera[0])

    def _move_camera(self, tag2camera):

        transform_manager = TransformManager()
        transform_manager.add("tag2camera", tag2camera)
        camera2tag = transform_manager.get("camera2tag")

        self.vtk_overlay_window.set_camera_pose(camera2tag)


class OverlayOnVideoFeed(OverlayBaseWidget):
    """
    Uses the acquired video feed as the background image,
    with no additional processing.
    """

    def update_view(self):
        """
        Get the next frame of input and display it.
        """
        _bool_retrieve, self.img = self.video_source.read()
        self.vtk_overlay_window.set_video_image(self.img)
        self.vtk_overlay_window.Render()

        if platform.system() == 'Linux':
            self.vtk_overlay_window.Initialize()
            self.vtk_overlay_window.Start()


# class OverlayOnVideoFeedCropRecord(OverlayBaseWidget):
#     """ Add cropping of the incoming video feed, and the ability to
#         record the vtk_overlay_window.
#
#        :param video_source: OpenCV compatible video source (int or filename)
#        :param output_filename: Location of output video file when recording.
#                                If none specified, the current date/time is
#                                used as the filename.
#     """
#
#     def __init__(self, video_source, output_filename=None, dims=None):
#         super().__init__(video_source, dims)
#         self.output_filename = output_filename
#         self.video_writer = None
#
#     def update_view(self):
#         """
#         Get the next frame of input, crop and/or
#         write to file (if either enabled).
#         """
#         _, self.img = self.video_source.read()
#
#         self.vtk_overlay_window.set_video_image(self.img)
#         self.vtk_overlay_window.Render()
#
#         if self.save_frame:
#             output_frame = self.get_output_frame()
#             self.video_writer.write_frame(output_frame,
#                                           self.video_source.timestamp)
#
#     def set_roi(self):
#         """
#            Crop the incoming video stream using ImageCropper.
#            Function is depreciated due to moving to opencv-headless
#            in sksurgeryvtk. I've left it in for the minute in case
#            any one is using it without my knowlegde
#         """
#         raise RuntimeError("Set Roi function is depreciated and",
#                            " is not longer implemented in sksurgeryutils")
#
#     def get_output_frame(self):
#         """ Get the output frame to write in numpy format."""
#         output_frame = \
#             self.vtk_overlay_window.convert_scene_to_numpy_array()
#         output_frame = cv2.cvtColor(output_frame, cv2.COLOR_RGB2BGR)
#
#         return output_frame
#
#     def on_record_start(self):
#         """ Start recording data on each frame update.
#         It is expected that this will be triggered using a Qt signal e.g. from
#         a button click. (see sksurgerydavinci.ui.Viewers for examples) """
#
#         # Set the filename to current date/time if no name specified.
#         if not self.output_filename:
#             self.output_filename = 'outputs/' + \
#                                    datetime.datetime.now().strftime( \
#                                        "%Y-%m-%d.%H-%M-%S") + '.avi'
#
#         output_frame = self.get_output_frame()
#         height, width = output_frame.shape[:2]
#         self.video_writer = TimestampedVideoWriter(self.output_filename,
#                                                    self.update_rate, width,
#                                                    height)
#         self.save_frame = True
#         logging.debug("Recording started.")
#
#     def on_record_stop(self):
#         """ Stop recording data. """
#         self.save_frame = False
#         self.video_writer.close()
#         logging.debug("Recording stopped.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # model_dir = './models'
    overlay_widget = OverlayBaseWidget(0)
    # overlay_widget.add_vtk_models_from_dir(model_dir)
    overlay_widget.show()
    overlay_widget.start()
    sys.exit(app.exec())
