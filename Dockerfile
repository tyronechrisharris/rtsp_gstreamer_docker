# Base image - Debian/Ubuntu based images are good for GStreamer
FROM ubuntu:22.04

# Set environment variables to prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.json

# Install Python, pip, GStreamer, and its Python bindings (PyGObject)
# Also install OpenCV dependencies and OpenCV itself via pip later
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-gi \
    python3-gst-1.0 \
    gir1.2-gst-rtsp-server-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    # OpenCV dependencies (subset, may need more depending on opencv-python variant)
    libgl1-mesa-glx \
    libglib2.0-0 \
    # For GObject Introspection and building some Python packages if needed
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    numpy \
    opencv-python-headless  # Headless version is good for servers

# Create app directory
WORKDIR /app

# Copy application files
COPY ./app/ /app/

# Expose the RTSP port (actual port mapping happens in `docker run`)
# This is more for documentation; the server will bind to the port specified in config.json
# EXPOSE 8554 # This will be dynamic based on config, so less useful here

# Command to run the application
ENTRYPOINT ["python3", "rtsp_server_gst.py"]