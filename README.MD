# COMP390

This project enables the overlaying of models onto video footage, which can be sourced from a camera, uploaded videos, and more. It incorporates model tracking with ArUco markers for precise positioning within the video frame. Primarily, the project is designed to complement Augmented Reality (AR) applications in the context of vascular cannulation surgery training and practice. It utilizes specific markers displayed within the view to pinpoint the model's location in AR headsets, ensuring synchronization between real-world and AR positions.

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

### Running Your Project

With the environment activated, you are now ready to run the project. Just run the main.py

## License

This project is licensed under the MIT License. For more details, see the `LICENSE` file.
