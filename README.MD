# Computer Vision and AR for Endovascular Intervention 

This project enables the overlaying of models onto video footage, which can be sourced from a camera, uploaded videos, and more. It incorporates model tracking with ArUco markers for precise positioning within the video frame. Primarily, the project is designed to complement Augmented Reality (AR) applications in the context of Endovascular Intervention surgery training and practice. It utilizes specific markers displayed within the view to pinpoint the model's location in AR headsets, ensuring synchronization between real-world and AR positions.

## Quick Start

This guide will assist you in installing Conda and setting up your project environment using the `env.yml` file.

### Installing Conda

First, ensure you have Conda installed on your computer. If not, follow these steps to install it:

1. Visit the [Miniconda website](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda website](https://www.anaconda.com/products/distribution) to download the installer.
2. Choose the appropriate version for your operating system and download it.
3. After downloading, follow the installation instructions provided on the page.

### Creating and Activating the Environment

Once Conda is installed, you can create and activate the environment with the `env.yml` file by following these steps:

1. Open the Terminal (Mac/Linux) or Command Prompt/PowerShell (Windows).
2. Navigate to the directory containing the `env.yml` file of the project.
3. Execute the following command to create the Conda environment:

```bash
conda env create -f env.yml
```

4. After the environment has been successfully created, activate it with the command:

```bash
conda activate track_env
```


# Usage

This document describes how to use two Python scripts: `Overlay_and_Tracking.py` and `Aruco_Generate.py`. These scripts are designed for overlaying and tracking in augmented reality (AR) applications and generating ArUco marker images, respectively.

## Overlay_and_Tracking.py

`Overlay_and_Tracking.py` is primarily used for real-time image overlay and object tracking within video streams. It utilizes ArUco markers for spatial positioning and camera calibration, making it suitable for applications requiring high interactivity and real-time performance, such as virtual reality (VR) and augmented reality (AR) in the context of Endovascular Intervention surgery training and practice.

### Main Features

- **Real-Time Video Capture**: Captures video streams from connected cameras.
- **Aruco Marker Detection**: Automatically detects ArUco markers in video frames, analyzing their positions and orientations.
- **Image Overlay**: Overlays graphics or other visual elements on the video frame based on the detected markers.
- **Spatial Tracking**: Uses detected markers for spatial positioning to support user interaction with the application.
- **Video Source Switching**: Allows switching between live camera feeds and uploaded video files, enabling flexible input sources for different testing or operational scenarios.
- **Model Color Modification**: Users can change the color of overlaid models dynamically, enhancing visual clarity or thematic consistency.
- **Aruco Marker Resizing**: Provides functionality to adjust the size of ArUco markers recognized by the system, accommodating various distances and camera specifications.
- **Different ArUco Marker Recognition**: Supports the ability to recognize different types of ArUco markers by selecting from various predefined dictionaries, ensuring adaptability to diverse application requirements.

## Aruco_Generate.py

`Aruco_Generate.py` offers a user interface for generating ArUco marker images of different types. It allows users to select different ArUco dictionaries and generate specific markers from those dictionaries. Generated images can be used for printing or as tracking markers.

### Main Features

- **Dictionary Selection**: Users can select different ArUco dictionaries via a dropdown menu, such as `DICT_4X4_50`, `DICT_6X6_100`, etc.
- **Real-Time Preview**: Upon dictionary selection, the script immediately generates an ArUco marker from the chosen dictionary and displays it within the interface.
- **Export Functionality**: Users can save the generated ArUco marker as an image file by clicking the "Save Marker" button, supporting both PNG and JPG formats.




## License

This project is licensed under the MIT License. For more details, see the `LICENSE` file.

##  Third-party libraries contained

SciKit-Surgery Augmented Reality
OpenCV
VTK
Numpy

