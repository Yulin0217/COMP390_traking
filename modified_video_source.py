import datetime
import cv2
import numpy as np
import sksurgerycore.utilities.validate_file as vf
import sksurgeryimage.utilities.camera_utilities as cu

class TimestampedVideoSource:
    def __init__(self, source_num_or_file, dims=None):
        self.source = cv2.VideoCapture(source_num_or_file)
        self.timestamp = None

        if not self.source.isOpened():
            raise RuntimeError("Failed to open Video camera:" + str(source_num_or_file))

        self.source_name = source_num_or_file

        # Setting dimensions if provided
        if dims:
            width, height = dims
            self.validate_dimensions(width, height)
            self.set_resolution(width, height)
        else:
            width = int(self.source.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.source.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.frame = np.empty((height, width, 3), dtype=np.uint8)
        self.ret = None

    def validate_dimensions(self, width, height):
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("Width and height must be integers")
        if width < 1 or height < 1:
            raise ValueError("Width and height must be >= 1")

    def set_resolution(self, width, height):
        self.source.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.source.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        set_w = self.source.get(cv2.CAP_PROP_FRAME_WIDTH)
        set_h = self.source.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if set_w != width or set_h != height:
            raise ValueError(f"Requested resolution {width}x{height} not supported, set to {set_w}x{set_h}.")

    def read(self):
        self.ret, self.frame = self.source.read()
        self.timestamp = datetime.datetime.now() if self.ret else None
        return self.ret, self.frame, self.timestamp

    def isOpened(self):
        return self.source.isOpened()

    def release(self):
        self.source.release()

    def update_source(self, new_source):
        self.release()
        self.__init__(new_source)

class VideoSourceWrapper:
    def __init__(self):
        self.sources = []

    def add_camera(self, camera_number, dims=None):
        cu.validate_camera_input(camera_number)
        self.add_source(camera_number, dims)

    def add_file(self, filename, dims=None):
        vf.validate_is_file(filename)
        self.add_source(filename, dims)

    def add_source(self, camera_num_or_file, dims=None):
        video_source = TimestampedVideoSource(camera_num_or_file, dims)
        self.sources.append(video_source)

    def are_all_sources_open(self):
        return all(source.isOpened() for source in self.sources)

    def release_all_sources(self):
        for source in self.sources:
            source.release()

    def get_next_frames(self):
        return [source.read()[1] for source in self.sources if source.isOpened()]
