# Dockerized RTSP Millisecond Clock & Connection Count Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) This project provides a cross-platform, Dockerized RTSP streaming server that generates a real-time video feed. The feed displays the current time with millisecond precision and the live count of active RTSP client connections. It's built using Python, GStreamer (specifically `gst-rtsp-server`), and OpenCV, designed for easy configuration and deployment.

The server dynamically creates video frames, encodes them, and streams them via RTSP, mimicking the behavior of a network security camera but with custom, dynamically generated content. Configuration is primarily handled by setting variables within the provided launch scripts, which are then passed as environment variables to the Docker container.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure the Server via Launch Scripts](#2-configure-the-server-via-launch-scripts)
  - [3. Build the Docker Image (Optional - Handled by Launch Scripts)](#3-build-the-docker-image-optional---handled-by-launch-scripts)
- [Running the Server](#running-the-server)
  - [Using Launch Scripts](#using-launch-scripts)
- [Connecting to the Stream](#connecting-to-the-stream)
- [Configuration Details (Environment Variables)](#configuration-details-environment-variables)
- [Docker Details](#docker-details)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements (Ideas)](#future-enhancements-ideas)
- [Contributing](#contributing)
- [License](#license)

## Features

* **Dynamic Video Content**:
    * Real-time clock display (Format: `HH:MM:SS.mmm`).
    * Live counter for active RTSP client connections.
    * High-contrast display: white block text on a black background.
* **RTSP Streaming**:
    * Robust streaming powered by GStreamer's `gst-rtsp-server` library.
    * Supports **H.264** and **MJPEG** video codecs.
    * Efficiently handles multiple concurrent client connections using a shared media pipeline.
* **Highly Configurable via Environment Variables**:
    * All critical server parameters are controlled by setting variables within the `launch.sh` and `launch.bat` scripts. These are then passed as environment variables to the Docker container.
    * Settings include RTSP authentication (username/password), server IP/port, video codec, resolution, FPS, H.264 GOP size, and RTSP stream path.
* **Dockerized for Portability**:
    * Runs within a Docker container, encapsulating all dependencies (GStreamer, OpenCV, Python, etc.).
    * `Dockerfile` provided for building a clean and consistent runtime environment.
* **Cross-Platform Launch Scripts**:
    * Includes `launch.sh` (for macOS/Linux) and `launch.bat` (for Windows) which simplify setting configuration and running the Docker container.
* **Local Operation**:
    * Designed to operate entirely locally without reliance on external APIs or internet resources (once the Docker image is built/pulled).

## Technology Stack

* **Primary Language**: Python 3
* **Media Framework**: GStreamer 1.0
    * RTSP Server: `gst-rtsp-server-1.0` library
    * Python Bindings: PyGObject (GObject Introspection for `gi.repository.Gst`, `gi.repository.GstRtspServer`)
* **Video Frame Generation**: OpenCV (`cv2`) for drawing text and creating image buffers.
* **Containerization**: Docker
* **Configuration Management**: Environment variables (set by launch scripts), with Python fallbacks to internal defaults.

## How It Works

The core of the application is a Python script (`rtsp_server_gst.py`) that initializes and runs a GStreamer RTSP server within a Docker container.
1.  **Configuration via Launch Scripts**: The user edits variables directly within `launch.sh` or `launch.bat`.
2.  **Environment Variables**: When the launch script is run, it passes these configuration settings as environment variables to the Docker container during the `docker run` command.
3.  **Configuration Loading in Python**: On startup, the Python application (`app/config_loader.py`) reads these environment variables. If specific environment variables are not set, it falls back to predefined default values.
4.  **Video Frame Generation**: The `VideoFrameGenerator` class (in `video_utils.py`) uses OpenCV to create raw video frames. Each frame contains the current timestamp (with milliseconds) and the count of currently connected RTSP clients.
5.  **GStreamer Media Factory**: A custom `ClockServerMediaFactory` constructs the GStreamer pipeline for the RTSP stream. This pipeline starts with an `appsrc` element, which is fed the dynamically generated video frames.
6.  **Encoding & Streaming**: Frames are then encoded (H.264 or MJPEG) and payloaded for RTSP streaming.
7.  **Client Connection Handling**: The server tracks connected clients and updates the count displayed in the video stream.
8.  **Docker Encapsulation**: The `Dockerfile` packages all necessary components.

## Project Structure


```

rtsp_gstreamer_docker/
├── app/                     # Python application source code
│   ├── rtsp_server_gst.py   # Main GStreamer RTSP server application
│   ├── video_utils.py       # Video frame generation logic
│   └── config_loader.py     # Configuration loading (from environment variables)
├── Dockerfile               # Defines the Docker image build process
├── config.json              # Reference/template configuration (not actively used by new launch scripts)
├── launch.sh                # Launch script for macOS/Linux (uses environment variables)
├── launch.bat               # Launch script for Windows (uses environment variables)
└── README.md                # This file

```

## Prerequisites

* **Docker**: Docker Desktop (for Windows/macOS) or Docker Engine (for Linux) must be installed and running. Download from [docker.com](https://www.docker.com/products/docker-desktop/).
* **Git**: For cloning the repository.
* **Text Editor**: For editing the configuration variables within `launch.sh` or `launch.bat`.

## Setup and Installation

### 1. Clone the Repository

Open your terminal or command prompt and clone the project:
```bash
git clone [https://github.com/tyronechrisharris/rtsp_gstreamer_docker.git](https://github.com/tyronechrisharris/rtsp_gstreamer_docker.git)
cd rtsp_gstreamer_docker

```

### 2. Configure the Server via Launch Scripts

Instead of editing `config.json` directly for deployment with the provided launch scripts, you will now **edit the launch script for your operating system** (`launch.sh` for macOS/Linux, `launch.bat` for Windows).

Open the relevant launch script in a text editor. At the top of the script, you will find a "Configuration Section" with variables like `RTSP_SERVER_PORT`, `RTSP_VIDEO_CODEC`, etc. Modify these variables to your desired settings.

**Example** section **in `launch.sh`:**

```
# --- Configuration Section ---
RTSP_VIEWER_USERNAME=""
RTSP_VIEWER_PASSWORD=""
RTSP_SERVER_IP="0.0.0.0"
RTSP_SERVER_PORT="8554"
# ... and so on
# --- End Configuration Section ---

```

An equivalent section exists in `launch.bat`.

### 3. Build the Docker Image (Optional - Handled by Launch Scripts)

The provided launch scripts will automatically attempt to build the Docker image (default name: `rtsp-clock-server:latest`) if it doesn't already exist. If you wish to build it manually:

```
docker build -t rtsp-clock-server:latest .

```

## Running the Server

### Using Launch Scripts

Ensure you have configured the variables inside your respective launch script as described in Step 2 above.

* **For macOS/Linux**:

  ```
  chmod +x launch.sh  # Make executable (if needed)
  ./launch.sh
  
  ```

* **For Windows**:

  ```
  .\launch.bat
  
  ```

The script will pass your configured settings as environment variables to the Docker container. The server will start, and you'll see log output in your terminal. To stop the server, press `Ctrl+C`.

## Connecting to the Stream

Once the server is running, connect using an RTSP client (like VLC Media Player):

`rtsp://<YOUR_HOST_IP_ADDRESS>:<PORT><STREAM_PATH>`

Where:

* `<YOUR_HOST_IP_ADDRESS>`: IP address of the machine running Docker (e.g., `localhost`, `127.0.0.1`, or your network IP).

* `<PORT>`: The `RTSP_SERVER_PORT` you set in the launch script.

* `<STREAM_PATH>`: The `RTSP_STREAM_PATH` you set in the launch script.

**Example URL (using default script values):** `rtsp://localhost:8554/live`

If authentication is enabled (by setting `RTSP_VIEWER_USERNAME` and `RTSP_VIEWER_PASSWORD` in the launch script), your client will prompt for credentials.

## Configuration Details (Environment Variables)

The Python application inside the Docker container reads the following environment variables. These are set by the `launch.sh` and `launch.bat` scripts based on the variables you define at the top of those scripts. If an environment variable is not set, the application will use an internal default.

| Environment Variable | Equivalent in `config.json` | Description | Default (in Python) | 
 | ----- | ----- | ----- | ----- | 
| `RTSP_VIEWER_USERNAME` | `viewerUsername` | Username for RTSP Basic authentication. If empty, authentication is disabled. | `""` (empty) | 
| `RTSP_VIEWER_PASSWORD` | `viewerPassword` | Password for RTSP Basic authentication. | `""` (empty) | 
| `RTSP_SERVER_IP` | `serverIPAddress` | IP address for the server to bind to *within the Docker container*. **Should typically be `"0.0.0.0"`**. | `"0.0.0.0"` | 
| `RTSP_SERVER_PORT` | `serverPort` | Port number for the RTSP server. | `8554` | 
| `RTSP_VIDEO_CODEC` | `videoCodec` | Video codec: `"h264"` or `"mjpeg"`. | `"h264"` | 
| `RTSP_VIDEO_RESOLUTION` | `videoResolution` | Video resolution, e.g., `"640x480"`, `"1280x720"`. | `"640x480"` | 
| `RTSP_FPS` | `framesPerSecond` | Desired frames per second. | `15` | 
| `RTSP_H264_GOP` | `h264IFrameInterval` | H.264 I-frame interval (GOP size) in frames. | `30` | 
| `RTSP_STREAM_PATH` | `rtspStreamPath` | RTSP URL path component (e.g., `/live`). | `"/live"` | 

The `config.json` file in the repository can still serve as a reference for these settings and their original structure.

## Docker Details

* **Image Name**: Default is `rtsp-clock-server:latest`.

* **Configuration**: Passed via environment variables (see above).

* **Ports**: The launch scripts map the `RTSP_SERVER_PORT` for TCP and UDP.

* **Dependencies**: The `Dockerfile` installs Python, GStreamer, OpenCV, and related libraries.

## Troubleshooting

* **Launch Script Errors on Windows (`to was unexpected at this time`, etc.)**: The current `launch.bat` uses environment variables directly and avoids complex parsing, which should resolve these issues. Ensure you are using the latest `launch.bat` from this project.

* **"Docker** command not **found"**: Ensure Docker is installed and in your system's PATH.

* **"Cannot connect to the Docker daemon"**: Make sure the Docker service/daemon is running.

* **Port Conflicts**: If the `RTSP_SERVER_PORT` is in use on your host, choose a different port in the launch script.

* **Stream Not Playing**:

  * Verify the RTSP URL, host IP, port, and path.

  * Check Docker container logs: `docker logs rtsp-clock-app` (if that's the container name).

  * Check host firewall settings.

* **Configuration Not Taking Effect**: Ensure you've correctly edited the variables at the top of the `launch.sh` or `launch.bat` script you are using. The Python application will print the configuration it has loaded (from environment variables or its defaults) to the console when it starts.

## Future Enhancements (Ideas)

* Support for multiple, distinctly configurable stream paths.

## Contributing

Contributions are welcome! Please Fork, Branch, Commit, and Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (if you add one).
If no `LICENSE` file is present, you might want to add one. A common choice for open-source projects is the MIT License. Example:

```
MIT License

Copyright (c) 2025 Tyrone Harris

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```



-----

```

