# Dockerized RTSP Millisecond Clock & Connection Count Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) This project provides a cross-platform, Dockerized RTSP streaming server that generates a real-time video feed. The feed displays the current time with millisecond precision and the live count of active RTSP client connections. It's built using Python, GStreamer (specifically `gst-rtsp-server`), and OpenCV, designed for easy configuration and deployment.

The server dynamically creates video frames, encodes them, and streams them via RTSP, mimicking the behavior of a network security camera but with custom, dynamically generated content.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Review Configuration](#2-review-configuration)
  - [3. Build the Docker Image (Optional - Handled by Launch Scripts)](#3-build-the-docker-image-optional---handled-by-launch-scripts)
- [Running the Server](#running-the-server)
  - [Using Launch Scripts](#using-launch-scripts)
  - [Manual Docker Run (Advanced)](#manual-docker-run-advanced)
- [Connecting to the Stream](#connecting-to-the-stream)
- [Configuration Details (`config.json`)](#configuration-details-configjson)
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
* **Highly Configurable**:
    * All critical server parameters are managed through an external `config.json` file.
    * Settings include RTSP authentication (username/password), server IP/port, video codec, resolution, FPS, H.264 GOP size, and RTSP stream path.
* **Dockerized for Portability**:
    * Runs within a Docker container, encapsulating all dependencies (GStreamer, OpenCV, Python, etc.).
    * `Dockerfile` provided for building a clean and consistent runtime environment.
* **Cross-Platform Launch Scripts**:
    * Includes `launch.sh` (for macOS/Linux) and `launch.bat` (for Windows) to simplify building the Docker image and running the container with the necessary volume mounts and port mappings.
* **Local Operation**:
    * Designed to operate entirely locally without reliance on external APIs or internet resources (once the Docker image is built/pulled).

## Technology Stack

* **Primary Language**: Python 3
* **Media Framework**: GStreamer 1.0
    * RTSP Server: `gst-rtsp-server-1.0` library
    * Python Bindings: PyGObject (GObject Introspection for `gi.repository.Gst`, `gi.repository.GstRtspServer`)
* **Video Frame Generation**: OpenCV (`cv2`) for drawing text and creating image buffers.
* **Containerization**: Docker
* **Configuration Management**: JSON (`config.json`)

## How It Works

The core of the application is a Python script (`rtsp_server_gst.py`) that initializes and runs a GStreamer RTSP server.
1.  **Configuration Loading**: On startup, the server reads its settings from the `config.json` file (mounted into the container).
2.  **Video Frame Generation**: The `VideoFrameGenerator` class (in `video_utils.py`) uses OpenCV to create raw video frames. Each frame contains the current timestamp (with milliseconds) and the count of currently connected RTSP clients.
3.  **GStreamer Media Factory**: A custom `ClockServerMediaFactory` (derived from `GstRtspServer.MediaFactory`) is defined. This factory is responsible for constructing the GStreamer pipeline for the RTSP stream when a client requests it.
    * The pipeline starts with an `appsrc` element. The Python application feeds the dynamically generated video frames (from step 2) into this `appsrc`.
    * Frames are then passed through `videoconvert` (for color space conversion if needed), an encoder (`x264enc` for H.264 or `jpegenc` for MJPEG), and finally a payloader (`rtph264pay` or `rtpjpegpay`) to prepare them for RTSP streaming.
4.  **Client Connection Handling**: The `gst-rtsp-server` library manages incoming client connections. Callbacks are used to:
    * Increment/decrement a connection counter.
    * Update the `VideoFrameGenerator` with the new connection count, so it's reflected in the video stream.
5.  **RTSP Server**: The server listens on the configured IP address and port, making the stream available at the specified path (e.g., `/live`). Authentication, if configured, is also handled by `gst-rtsp-server`.
6.  **Docker Encapsulation**: The `Dockerfile` packages the Python application, GStreamer libraries, OpenCV, and all other dependencies into a portable container image.

## Project Structure

```

rtsp\_gstreamer\_docker/
├── app/                     \# Python application source code
│   ├── rtsp\_server\_gst.py   \# Main GStreamer RTSP server application
│   ├── video\_utils.py       \# Video frame generation logic
│   └── config\_loader.py     \# Configuration file loading and validation
├── Dockerfile               \# Defines the Docker image build process
├── config.json              \# Sample/default server configuration (mounted from host)
├── launch.sh                \# Launch script for macOS/Linux
├── launch.bat               \# Launch script for Windows
└── README.md                \# This file

````

## Prerequisites

* **Docker**: Docker Desktop (for Windows/macOS) or Docker Engine (for Linux) must be installed and running. Download from [docker.com](https://www.docker.com/products/docker-desktop/).
* **Git**: For cloning the repository.
* **Text Editor**: For viewing/editing `config.json`.

## Setup and Installation

### 1. Clone the Repository

Open your terminal or command prompt and clone the project:
```bash
git clone https://github.com/tyronechrisharris/rtsp_gstreamer_docker.git
cd rtsp_gstreamer_docker
````

### 2\. Review Configuration

Before running the server, inspect and customize the `config.json` file located in the root of the cloned project. This file controls all aspects of the server. See the [Configuration Details](https://www.google.com/search?q=%23configuration-details-configjson) section below for an explanation of each parameter.

**Example `config.json`:**

```json
{
    "viewerUsername": "user",
    "viewerPassword": "password",
    "serverIPAddress": "0.0.0.0",
    "serverPort": 8554,
    "videoCodec": "h264",
    "videoResolution": "1280x720",
    "framesPerSecond": 25,
    "h264IFrameInterval": 50,
    "rtspStreamPath": "/live"
}
```

  * **Important for Docker**: `serverIPAddress` should generally be kept as `"0.0.0.0"` to allow the server within the Docker container to listen on all its network interfaces. The port mapping in Docker will handle exposing it to your host.

### 3\. Build the Docker Image (Optional - Handled by Launch Scripts)

The provided launch scripts (`launch.sh` and `launch.bat`) will automatically attempt to build the Docker image if it doesn't already exist. However, if you wish to build it manually:

```bash
docker build -t rtsp-clock-server:latest .
```

(The default image name used by the scripts is `rtsp-clock-server:latest`)

## Running the Server

### Using Launch Scripts

The easiest way to run the server is by using the provided launch scripts. These scripts handle:

  * Checking for and building the Docker image if needed.

  * Reading the `serverPort` from `config.json` for correct port mapping.

  * Mounting your local `config.json` into the container (read-only).

  * Running the Docker container with appropriate port mappings for TCP and UDP (RTSP uses both).

  * **For macOS/Linux**:

    ```bash
    chmod +x launch.sh  # Make executable (if needed)
    ./launch.sh
    ```

  * **For Windows**:

    ```batch
    launch.bat
    ```

The server will start, and you'll see log output in your terminal. To stop the server, press `Ctrl+C` in the terminal where the script is running. The container is set to be removed automatically on exit (`--rm`).

### Manual Docker Run (Advanced)

If you prefer to run the Docker container manually (e.g., for custom Docker options or if not using the launch scripts), you can use a command similar to this:

```bash
# Replace <HOST_PORT> with the port you want to expose on your host machine.
# Replace <CONFIG_FILE_PATH_ON_HOST> with the absolute path to your config.json.
# Example for Linux/macOS:
docker run -it --rm \
    --name rtsp-clock-app \
    -v "<CONFIG_FILE_PATH_ON_HOST>/config.json":/app/config.json:ro \
    -p "<HOST_PORT>:<CONFIG_SERVER_PORT>/tcp" \
    -p "<HOST_PORT>:<CONFIG_SERVER_PORT>/udp" \
    rtsp-clock-server:latest

# Example for Windows (using PowerShell syntax for path):
# docker run -it --rm `
#    --name rtsp-clock-app `
#    -v "${PWD}/config.json":/app/config.json:ro `
#    -p "<HOST_PORT>:<CONFIG_SERVER_PORT>/tcp" `
#    -p "<HOST_PORT>:<CONFIG_SERVER_PORT>/udp" `
#    rtsp-clock-server:latest
```

  * `<CONFIG_SERVER_PORT>` is the `serverPort` value from your `config.json`.
  * Ensure the path to `config.json` is correct.
  * The launch scripts automate deriving `<HOST_PORT>` and `<CONFIG_SERVER_PORT>` from `config.json`.

## Connecting to the Stream

Once the server is running, you can connect to the RTSP stream using any RTSP-compatible media player, such as:

  * **VLC Media Player** (Recommended)
  * FFmpeg/FFplay
  * GStreamer `gst-launch-1.0` or `gst-play-1.0`

The stream URL will be:
`rtsp://<YOUR_HOST_IP_ADDRESS>:<PORT><STREAM_PATH>`

Where:

  * `<YOUR_HOST_IP_ADDRESS>`: This is the IP address of the machine running Docker (e.g., `localhost` or `127.0.0.1` if accessing from the same machine, or the network IP like `192.168.1.100` if accessing from another device on the same network).
  * `<PORT>`: The `serverPort` specified in your `config.json` (and mapped by Docker).
  * `<STREAM_PATH>`: The `rtspStreamPath` specified in your `config.json` (e.g., `/live`).

**Example URL (using default config values):** `rtsp://localhost:8554/live`

If you have enabled authentication in `config.json` (by providing `viewerUsername` and `viewerPassword`), your RTSP client will prompt you for these credentials.

## Configuration Details (`config.json`)

The `config.json` file allows you to customize the server's behavior.

| Parameter             | Type   | Description                                                                                                   | Default Value     |
| --------------------- | ------ | ------------------------------------------------------------------------------------------------------------- | ----------------- |
| `viewerUsername`      | string | Username for RTSP Basic authentication. If empty, authentication is disabled.                                 | `""` (empty)      |
| `viewerPassword`      | string | Password for RTSP Basic authentication. Used only if `viewerUsername` is not empty.                           | `""` (empty)      |
| `serverIPAddress`     | string | IP address for the server to bind to *within the Docker container*. **Should typically be `"0.0.0.0"`**.      | `"0.0.0.0"`       |
| `serverPort`          | integer| Port number for the RTSP server to listen on. This port will be mapped from the host by Docker.               | `8554`            |
| `videoCodec`          | string | Video codec to use. Supported values: `"h264"` or `"mjpeg"`.                                                  | `"h264"`          |
| `videoResolution`     | string | Video resolution in `WIDTHxHEIGHT` format (e.g., `"640x480"`, `"1280x720"`, `"1920x1080"`).                     | `"640x480"`       |
| `framesPerSecond`     | integer| Desired frames per second for the output stream.                                                              | `15`              |
| `h264IFrameInterval`  | integer| I-frame interval (GOP - Group of Pictures size) in frames, if H.264 codec is used. Affects stream seekability. | `30`              |
| `rtspStreamPath`      | string | The path component of the RTSP URL where the stream will be available (e.g., `/live`, `/cam1`).                 | `"/live"`         |

## Docker Details

  * **Image Name**: The default image name used by the scripts and `Dockerfile` is `rtsp-clock-server:latest`.
  * **Environment Variable**: `CONFIG_PATH` is set within the `Dockerfile` to `/app/config.json`, which is where the application expects to find the mounted configuration file.
  * **Ports**: The RTSP server requires both TCP (for RTSP control commands) and UDP (for RTP/RTCP media streaming) ports to be mapped. The launch scripts handle mapping the `serverPort` from `config.json` for both protocols.
  * **Dependencies**: The `Dockerfile` installs:
      * Python 3 and pip.
      * GStreamer libraries (`gstreamer1.0-plugins-base/good/bad/ugly`, `gstreamer1.0-libav`).
      * GStreamer RTSP server library (`gir1.2-gst-rtsp-server-1.0`).
      * Python GObject bindings (`python3-gi`, `python3-gst-1.0`).
      * OpenCV (headless version via pip: `opencv-python-headless`) and NumPy.

## Troubleshooting

  * **"Docker command not found"**: Ensure Docker is installed and its command-line tools are in your system's PATH.
  * **"Cannot connect to the Docker daemon"**: Make sure the Docker service/daemon is running.
  * **Port Conflicts**: If the `serverPort` specified in `config.json` is already in use on your host machine, Docker will fail to map it. Choose a different port in `config.json` or stop the conflicting service. The launch scripts will use this new port for mapping.
  * **Stream Not Playing in VLC**:
      * Verify the RTSP URL is correct (IP address, port, path).
      * Check the Docker container logs for any errors from GStreamer or Python. You can view logs via `docker logs rtsp-clock-app` if the container is running detached or if you re-attach.
      * Ensure your firewall is not blocking connections to the mapped port on your host.
      * Try a simpler configuration (e.g., lower resolution, MJPEG codec) to see if it works.
  * **Incorrect `config.json` Path**: If the server reports it's using default settings or cannot find `config.json`, double-check the volume mount path in your `docker run` command or ensure the launch scripts are executed from the project's root directory.
  * **Authentication Issues**: If authentication is enabled, ensure you are entering the correct username and password in your RTSP client.
  * **Performance on Low-Power Devices**: H.264 encoding can be CPU-intensive. If running on a resource-constrained host (like a Raspberry Pi), you might need to use lower resolutions/FPS or switch to MJPEG. The `x264enc speed-preset=ultrafast tune=zerolatency` settings are chosen for low latency but might not offer the best compression.

## Future Enhancements (Ideas)

  * Support for more video codecs (e.g., VP8, VP9).
  * More advanced text styling options (fonts, colors, positioning).
  * Ability to overlay a custom logo or image.
  * REST API for querying server status or dynamically updating some non-critical parameters.
  * More sophisticated authentication mechanisms (e.g., Digest authentication).
  * Support for multiple, distinctly configurable stream paths from a single server instance.
  * Improved error handling and logging.

## Contributing

Contributions are welcome\! If you have improvements, bug fixes, or new features you'd like to add, please feel free to:

1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

Please try to follow existing code style and add comments where necessary.

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
```
