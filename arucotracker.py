from time import time
from numpy import array, float32, loadtxt, ravel, float64
from cv2 import aruco
import cv2
from imshowtk.imshowtk import ImshowTk as Debugger

from sksurgerycore.baseclasses.tracker import SKSBaseTracker
from sksurgeryarucotracker.algorithms.rigid_bodies import ArUcoRigidBody, \
                configure_rigid_bodies

def _load_calibration(textfile):

    projection_matrix = loadtxt(textfile, dtype=float32, max_rows=3)
    distortion = loadtxt(textfile, dtype=float32, skiprows=3, max_rows=1)

    return projection_matrix, distortion

class ArUcoTracker(SKSBaseTracker):
    def __init__(self, configuration):

        self._camera_projection_matrix = configuration.get("camera projection",
                                                           None)
        self._camera_distortion = configuration.get(
                        "camera distortion", array([0.0, 0.0, 0.0, 0.0, 0.0],
                                                   dtype=float32))
        self._state = None

        self._frame_number = 0

        self._debug = Debugger(configuration.get("debug", False),
                configuration.get("debug subsample", 4))

        video_source = configuration.get("video source", 0)

        if video_source != 'none':
            self._capture = cv2.VideoCapture()
        else:
            self._capture = None

        self._ar_dicts, self._ar_dict_names, self._rigid_bodies = \
                        configure_rigid_bodies(configuration)

        super().__init__(configuration, self._rigid_bodies)
        self._marker_size = configuration.get("marker size", 50)

        if "calibration" in configuration:
            self._camera_projection_matrix, self._camera_distortion = \
                _load_calibration(configuration.get("calibration"))

        self._check_pose_estimation_ok()

        if video_source != 'none':
            if self._capture.open(video_source):
                if "capture properties" in configuration:
                    props = configuration.get("capture properties")
                    for prop in props:
                        cvprop = getattr(cv2, prop)
                        value = props[prop]
                        self._capture.set(cvprop, value)

                self._state = "ready"
            else:
                raise OSError(f'Failed to open video source {video_source}')
        else:
            self._state = "ready"


    def _check_pose_estimation_ok(self):
        if self._camera_projection_matrix is None:
            return

        if (self._camera_projection_matrix.shape == (3, 3) and
                (self._camera_projection_matrix.dtype in [float32,
                        float64, float])):
            return

        raise ValueError(('Camera projection matrix needs to be 3x3 and'
                          'float32'), self._camera_projection_matrix.shape,
                          self._camera_projection_matrix.dtype)

    def close(self):
        if self._capture is not None:
            self._capture.release()
            del self._capture
        self._state = None

    def get_frame(self, frame=None):
        if self._state != "tracking":
            raise ValueError('Attempted to get frame, when not tracking')

        if self._capture is not None:
            _, frame = self._capture.read()

        if frame is None:
            raise ValueError('End of video')



        port_handles = []
        time_stamps = []
        frame_numbers = []
        tracking_rots = []
        tracking_trans = []
        quality = []
        self._reset_rigid_bodies()

        timestamp = time()


        temporary_rigid_bodies = []
        for dict_index, ar_dict in enumerate(self._ar_dicts):
            marker_corners, marker_ids, _ = \
                    aruco.detectMarkers(frame, ar_dict)
            if not marker_corners:
                self._debug.imshow(frame)
                continue

            if self._debug.in_use:
                aruco.drawDetectedMarkers(frame, marker_corners)
                self._debug.imshow(frame)

            assigned_marker_ids = []
            for rigid_body in self._rigid_bodies:
                if rigid_body.get_dictionary_name() == \
                                self._ar_dict_names[dict_index]:
                    assigned_marker_ids.extend(rigid_body.set_2d_points(
                                    marker_corners, marker_ids))

            #find any unassigned tags and create a rigid body for them
            for index, marker_id in enumerate(marker_ids):
                if marker_id[0] not in ravel(assigned_marker_ids):
                    temp_rigid_body = ArUcoRigidBody(
                                    str(self._ar_dict_names[dict_index]) +
                                    ":" + str(marker_id[0]))
                    temp_rigid_body.add_single_tag(self._marker_size,
                                    marker_id[0], ar_dict)
                    temp_rigid_body.set_2d_points([marker_corners[index]],
                                    marker_id)
                    temporary_rigid_bodies.append(temp_rigid_body)

        for rigid_body in self._rigid_bodies + temporary_rigid_bodies:
            rb_rot, rb_trans, rbquality = rigid_body.get_pose(
                             self._camera_projection_matrix,
                             self._camera_distortion)
            port_handles.append(rigid_body.name)
            time_stamps.append(timestamp)
            frame_numbers.append(self._frame_number)
            tracking_rots.append(rb_rot)
            tracking_trans.append(rb_trans)
            quality.append(rbquality)

        self.add_frame_to_buffer(port_handles, time_stamps,
                    frame_numbers,
                    tracking_rots, tracking_trans, quality,
                    rot_is_quaternion = False)

        self._frame_number += 1
        return self.get_smooth_frame(port_handles)

    def get_tool_descriptions(self):
        return "No tools defined"

    def start_tracking(self):
        if self._state == "ready":
            self._state = "tracking"
        else:
            raise ValueError('Attempted to start tracking, when not ready')

    def stop_tracking(self):
        if self._state == "tracking":
            self._state = "ready"
        else:
            raise ValueError('Attempted to stop tracking, when not tracking')

    def _reset_rigid_bodies(self):
        for rigid_body in self._rigid_bodies:
            rigid_body.reset_2d_points()

    def has_capture(self):
        if self._capture is None:
            return False
        return True
